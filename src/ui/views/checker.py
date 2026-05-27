from src.ui.base_view import BaseView


class CheckerView(BaseView):
    def __init__(self):
        super().__init__(
            'Чек на валид - показывает какие аккаунты живые, а какие стухли. Дополнительные проверки включаются по необходимости:звезды, баланс крипто-ботов, премиум и админ каналы.'
        )
