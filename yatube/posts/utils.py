from django.conf import settings
from django.core.paginator import Paginator


def paging(post_list, request):
    paginator = Paginator(post_list, settings.POSTS_ON_PAGE)
    page_number = request.GET.get('page')
    return paginator.get_page(page_number)
