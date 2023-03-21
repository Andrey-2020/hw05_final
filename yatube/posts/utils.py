from django.conf import settings
from django.core.paginator import Paginator


def paginate_queryset(request, list):
    paginator = Paginator(list, settings.POSTS_TO_OUTPUT)
    page_number = request.GET.get('page')

    return paginator.get_page(page_number)
