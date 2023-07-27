from django.db.models.signals import m2m_changed, pre_delete, pre_save
from django.dispatch import receiver
from T.models import Plaque, Celebrity, User
import logging

@receiver(m2m_changed, sender=Plaque.celebrities.through)
def callback_m2m(sender, instance, action, *args, **kwargs):
    if action in ["post_remove"]:
        for cel in Celebrity.objects.filter(pk__in=kwargs["pk_set"]):
            if not cel.plaque_set.exists():
                try:
                    cel.delete()
                except:
                    logging.error("", exc_info=True)


@receiver(pre_delete, sender=Plaque)
def callback_pre_delete(sender, instance, *args, **kwargs):
    for cel in instance.celebrities.all():
        if cel.plaque_set.count() == 1:
            cel.delete()


@receiver(pre_save, sender=User)
def callback_pre_save(sender, instance, *args, **kwargs):
    if not instance.phone.startswith("+"):
        instance.phone = "+" + instance.phone
