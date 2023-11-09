from typing import List

from django.contrib.auth.models import AbstractUser
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import models
from django.shortcuts import get_object_or_404
from django.utils import timezone


class User(AbstractUser):
    status = models.CharField(max_length=255)


class UserSettings(models.Model):
    user = models.OneToOneField(to=get_user_model(), on_delete=models.CASCADE)


class Voting(models.Model):
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)

    """
    1 - one of many
    2 - some of many
    3 - discrete
    """
    type = models.IntegerField(default=3)
    name = models.CharField(max_length=63)
    description = models.CharField(max_length=255)
    published = models.BooleanField(default=False)

    def get_all_variants(self):
        return self.votevariant_set.all()

    def count_all_facts(self):
        count = 0
        for variant in self.get_all_variants():
            count += variant.get_all_facts().count()
        return count

    def user_has_already_voted(self, user):
        variants = self.get_all_variants()
        return VoteFactVariant.objects.filter(fact__user=user, variant__in=variants).count() > 0

    def make_votefact(self, variant_ids_list: List[int], author: User) -> None:
        if len(variant_ids_list) == 0:
            raise PermissionError('Не указаны варианты, за которые голосуем')

        if self.user_has_already_voted(author):
            raise PermissionError('Пользователь уже голосовал в этом голосовании')

        for variant_id in variant_ids_list:
            variant = get_object_or_404(VoteVariant, id=variant_id)
            if variant.voting != self:
                raise PermissionError('Этот вариант не принадлежит текущему голосованию')

        if self.type in [1, 3] and len(variant_ids_list) > 1:
            raise PermissionError('Нельзя оставлять голос за несколько вариантов в голосовании с данным типом')

        record = VoteFact(user=author)
        record.save()

        for variant_id in variant_ids_list:
            variant = get_object_or_404(VoteVariant, id=variant_id)
            factvariant_record = VoteFactVariant(fact=record, variant=variant)
            factvariant_record.save()

    def delete_variant(self, variant_id, user):
        variant_set = self.votevariant_set.filter(id=variant_id)
        if variant_set.count() == 0:
            raise PermissionError('Попытка удалить вариант, не принадлежащий этому голосованию')
        if self.author != user and not user.is_staff:
            raise PermissionError('У вас нет разрешения для удаления этого варианта')

        variant = variant_set.first()
        fact_variants = variant.votefactvariant_set.all()
        facts = [v.fact for v in fact_variants]
        for fact in facts:
            if fact.votefactvariant_set.count() == 1:
                fact.delete()
        # сами votefactvariant'ы не удаляем, их каскадом зацепит

        variant.delete()

    @staticmethod
    def create(author, name, description, voting_type, variants):
        if voting_type not in ['1', '2', '3']:
            raise ValidationError('Поле типа может принимать значения только 1, 2 или 3')
        voting = Voting(author=author, name=name, description=description, type=int(voting_type))
        voting.save()
        for variant in variants:
            variant_record = VoteVariant(voting=voting, description=variant)
            variant_record.save()
        return voting

    def get_results(self):
        facts = {}
        count = self.count_all_facts()
        for variant in self.get_all_variants():
            variant_count = variant.get_all_facts().count()
            facts[variant] = {
                'count': variant_count,
                'percentage': variant_count / count if count else 0
            }
        return facts


class VoteVariant(models.Model):
    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    description = models.CharField(max_length=127)

    def get_all_facts(self):
        return self.votefactvariant_set.all()


class VoteFact(models.Model):
    user = models.ForeignKey(to=User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(default=timezone.now)

    def get_voting(self):
        return self.votefactvariant_set.first().variant.voting


class VoteFactVariant(models.Model):
    fact = models.ForeignKey(to=VoteFact, on_delete=models.CASCADE)
    variant = models.ForeignKey(to=VoteVariant, on_delete=models.CASCADE)


class Complaint(models.Model):
    author = models.ForeignKey(to=User, on_delete=models.CASCADE)
    voting = models.ForeignKey(to=Voting, on_delete=models.CASCADE)
    description = models.CharField(max_length=2000)
    status = models.IntegerField(default=0)
