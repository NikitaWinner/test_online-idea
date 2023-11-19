import logging
import re
from typing import Set, Tuple

from django.core.cache import cache
from django.db import transaction
from django.shortcuts import render
from django.views import View
from lxml import etree
from .forms import BrandForm
from .models import Model, Brand


class HomeView(View):
    """
    Класс представления для отображения главной страницы.
    """

    template_name = 'catalog_app/home.html'

    def get(self, request, *args, **kwargs):
        """
        Обработчик GET-запроса для отображения формы выбора марки.
        """
        form = BrandForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request, *args, **kwargs):
        """
        Обработчик POST-запроса для обработки формы выбора марки.
        """
        form = BrandForm(request.POST)
        models_for_brand = None

        if form.is_valid():
            selected_brand = form.cleaned_data['brand']

            # Пробуем получить выборку моделей из кэша и проверяем
            cache_key = f'models_for_brand_{selected_brand.pk}'
            models_for_brand = cache.get(cache_key)

            if models_for_brand is None:
                # Если нет в кэше, делаем запрос к бд
                models_for_brand = Model.objects.filter(brand=selected_brand)

                # Сохраняем выборку в кэше
                cache.set(cache_key, models_for_brand)

        return render(request, self.template_name, {'form': form, 'models_for_mark': models_for_brand})


class UpdateCatalogView(View):
    """
    Класс представления для обновления каталога авто.
    """

    template_name = 'catalog_app/update_success.html'
    logger = logging.getLogger(__name__)

    def get_data_from_xml(self) -> Tuple[Set[Brand], Set[Model]]:
        """
        Получает данные из XML-файла и обновляет базу данных.

        :return: Множества объектов CarBrand и CarModel.
        """
        try:
            # Очистка базы данных перед обновлением
            Brand.objects.all().delete()
            Model.objects.all().delete()

            # Читаем файл
            tree = etree.parse('cars.xml')
            root = tree.getroot()

            # Переменные для объектов из базы
            data_brand: Set[Brand] = set()
            data_model: Set[Model] = set()

            # Для гарантии атомарности операций при обновлении
            with transaction.atomic():
                # Итерируемся по всем элементам mark по отношению к текущему узлу(root)
                for mark_elem in root.xpath('//mark'):
                    name_brand = mark_elem.get('name')
                    brand = Brand.objects.create(name=name_brand)
                    data_brand.add(brand)

                    # Итерируемся по всем элементам folder по отношению к текущему узлу(mark)
                    for folder_elem in mark_elem.xpath('.//folder'):
                        name_model = folder_elem.get('name').split(',')[0].strip()

                        # Очистка от лишних символов для кэша
                        model_key = re.sub(r'\W+', '', f"{name_brand}{name_model}")

                        # Проверяем, есть ли модель в кэше
                        if cache.get(model_key) is None:
                            # Если нет, то создаем и добавляем в кэш
                            model = Model.objects.create(brand=brand, name=name_model)
                            cache.set(model_key, model)

                            data_model.add(model)

                            # Удаляем старый ключ из кэша, который хранит queryset моделей авто
                            # (он обновится при post запросе по маршруту home/)
                            cache.delete(f'models_for_brand_{brand.pk}')

            self.logger.info("Данные успешно обновлены")
            return data_brand, data_model
        except Exception as e:
            self.logger.exception(f"Ошибка при обновлении данных: {e}")

    def get(self, request, *args, **kwargs):
        """
        Обработчик GET-запроса для отображения данных обновления.
        """
        brands, models = self.get_data_from_xml()

        context = {
            'all_brands': len(brands),
            'all_models': len(models),
        }

        return render(request, self.template_name, context)
