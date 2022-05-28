import modelqueue
import tree_sitter_languages as ts

from pygments import highlight
from pygments.lexers import TextLexer, get_lexer_for_filename
from pygments.formatters import HtmlFormatter
from pygments.util import ClassNotFound as PygmentsClassNotFound

from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render

from .forms import SearchForm, SourceForm
from .models import Search, Source

EXTENSIONS = {'py': 'python', 'java': 'java'}


def index(request):
    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            search = form.save()
            return redirect('search', search_id=search.id)
    else:
        form = SearchForm()
    searches = Search.objects.order_by('-create_time')[:10]
    return render(request, 'tree_sitter_server/index.html', {'searches': searches})


def search(request, search_id):
    search = get_object_or_404(Search, pk=search_id)
    if request.method == 'POST':
        action = request.POST.get('action', '')
        if action == 'rerun':
            search.status = modelqueue.Status.waiting()
            search.save()
            return redirect('search', search_id=search.id)
        else:
            assert action == 'delete'
            search.delete()
            return redirect('index')
    return render(request, 'tree_sitter_server/search.html', {'search': search})


def source(request, path):
    if path != '':
        return source_path(request, path)
    return source_form(request, path)


def source_path(request, path):
    source = get_object_or_404(Source, path=path)
    try:
        lexer = get_lexer_for_filename(path)
    except PygmentsClassNotFound:
        lexer = TextLexer()
    formatter = HtmlFormatter(
        linenos=True,
        lineanchors='line',
        anchorlinenos=True,
    )
    code = highlight(source.text, lexer, formatter)
    style = formatter.get_style_defs()
    parser = ts.get_parser('python')
    tree = parser.parse(source.text.encode())
    node = tree.root_node
    sexp = node.sexp()
    parts = sexp.split()
    indent = 0
    for index in range(len(parts)):
        part = parts[index]
        parts[index] = ' ' * (indent * 2) + part
        indent += part.count('(') - part.count(')')
    sexp = '\n'.join(parts)
    context = {'source': source, 'code': code, 'style': style, 'sexp': sexp}
    return render(request, 'tree_sitter_server/source-path.html', context)


def source_form(request, path):
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            source = form.save(commit=False)
            if source.language == 'language':
                extension = source.language.split('.')[-1]
                language = EXTENSIONS[extension]
                source.language = language
            with transaction.atomic():
                Source.objects.filter(path=source.path).delete()
                source.save()
            return redirect('source', path=source.path)
    else:
        form = SourceForm()
    sources = Source.objects.order_by('-update_time')[:10]
    context = {'form': form, 'sources': sources}
    return render(request, 'tree_sitter_server/source-form.html', context)
