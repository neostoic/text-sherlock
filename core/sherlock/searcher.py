""" 
searcher.py
Created by: Christopher Bess
Copyright: 2011
"""

from whoosh.qparser import QueryParser
# from whoosh.query import And, Term
from whoosh import highlight
from core.sherlock import logger as log
from core.utils import debug, read_file
import settings


class Searcher(object):
    def __init__(self, indexer):
        self._indexer = indexer
        self._index = indexer.index()
        pass
    
    def find_text(self, text, pagenum=1, limit=10):
        """Finds the specified text by searching the internal index
        """
        log.debug('searching for: %s' % text)
        parser = QueryParser('content', self._index.schema)
        query = parser.parse(unicode(text))
        return self.search(query, pagenum, limit)
        
    def search(self, squery, pagenum=1, limit=10):
        """Searches the internal index using the specified query
        @param QueryParser squery
        """
        assert self._index is not None
        log.debug('search page %d, limit %d' % (pagenum, limit))
        results = None
        with self._index.searcher() as searcher:
            page = searcher.search_page(squery, pagenum, limit, terms=True)
            results = self._get_results(page)
        return results
        
    def _get_results(self, results_page):
        """Populates the results with normalized Sherlock result data
        @param whoosh.ResultsPage results_page
        @return tuple of sherlock.Result objects
        """
        results = []
        hits = results_page.results
        hits.fragmenter = ResultFragmenter()
        hits.formatter = ResultFormatter()
        for hit in hits:
            result = Result(hit, **hit.fields())
            results.append(result)
        return results


class Result(object):
    """Represents a sherlock result
    """
    def __init__(self, hit, **kwargs):
        """Initializes this Result instance
        @param whoosh.Hit hit The hit this instance represents
        @param kwargs {
            path = Path of the file this result represents
            filename = Filename of the file
        }
        """
        # the textual context of the hit
        self._context = ''
        self._path = kwargs['path']
        self._filename = kwargs['filename']
        self._process_hit(hit)
        pass
        
    def _process_hit(self, hit):
        """Process the result data, reads the original file to produce
        the context
        @remark For now it only processes to get the context for the result
        """
        contents = read_file(self.path)
        self._context = hit.highlights('content', text=contents)
        pass
        
    @property
    def path(self):
        """path
        """
        return self._path
        
    @property
    def filename(self):
        """filename
        """
        return self._filename
        
    @property
    def context(self):
        """context
        """
        return self._context


# refs:
# https://bitbucket.org/mchaput/whoosh/src/4470a8812c9e/src/whoosh/highlight.py
# http://packages.python.org/Whoosh/api/highlight.html?highlight=hit#manual-highlighting
class ResultFragmenter(highlight.Fragmenter):
    def fragment_tokens(self, text, all_tokens):
        tokens = []
        for tk in all_tokens:
            tokens.append(tk.copy())
            if tk.matched:
                yield highlight.mkfrag(text, tokens, startchar=tk.startchar, endchar=tk.endchar)


class ResultFormatter(highlight.Formatter):
    max_lines = settings.NUM_CONTEXT_LINES # fragment context
    new_line = settings.NEW_LINE
    
    def format_token(self, text, token, replace=False):
        token_text = text[token.startchar:token.endchar]
        return '<strong>%s</strong>' % token_text

    def fragement_text(self, fragment):
        """Returns the text for the specified fragment
        """
        assert self.max_lines > 0
        token = fragment # alias
        text = token.text
        nl = self.new_line
        # add the formatted token
        bText = text[:token.startchar]
        eText = text[token.endchar:]
        text = u''.join((bText, self.format_token(text, token), eText))
        # get the position up to the previous new line
        prevIdx = text.rfind(nl, 0, token.startchar)
        # get the position of the next new line
        nextIdx = text.find(nl, token.endchar)
        # should we try to get more lines
        if self.max_lines > 1:
            idx = prevIdx
            line = 1
            # lines before token
            while idx >= 0 and line <= self.max_lines:
                prevIdx = idx
                idx = text.rfind(nl, 0, prevIdx)
                line += 1
            # lines after token
            idx = nextIdx
            line = 1
            while idx >= 0 and line <= self.max_lines:
                nextIdx = idx + 1
                idx = text.find(nl, nextIdx)
                line += 1
        # get token and context
        if prevIdx < 0:
            prevIdx = 0
        token_text = text[prevIdx:nextIdx]
        return token_text

    def format(self, fragments, replace=False):
        lines = []
        for fragment in fragments:
            context = self.fragement_text(fragment)
            lines.append(context)
        final_text = u''.join(lines)
        return final_text

        