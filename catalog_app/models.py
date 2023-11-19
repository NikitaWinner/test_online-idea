from django.db import models


class Brand(models.Model):
    """
    Модель для представления марки автомобиля.
    """

    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class Model(models.Model):
    """
    Модель для представления модели автомобиля.
    """

    name = models.CharField(max_length=255)
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE)

    def __str__(self):
        return self.name
