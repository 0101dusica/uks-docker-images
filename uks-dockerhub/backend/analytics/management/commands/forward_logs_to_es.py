import hashlib
import json
import logging

from django.conf import settings
from django.core.management.base import BaseCommand
from elasticsearch import Elasticsearch, ConnectionError as ESConnectionError
from elasticsearch.helpers import bulk

logger = logging.getLogger('analytics.forward_logs_to_es')


class Command(BaseCommand):
    help = 'Forward new JSON log lines from django.log to Elasticsearch.'

    @staticmethod
    def _log_path():
        return settings.LOG_DIR / 'django.log'

    @staticmethod
    def _cursor_path():
        return settings.LOG_DIR / '.es_cursor'

    def _read_cursor(self):
        try:
            return int(self._cursor_path().read_text().strip())
        except (FileNotFoundError, ValueError):
            return 0

    def _write_cursor(self, offset: int):
        self._cursor_path().write_text(str(offset))

    def handle(self, *args, **options):
        log_path = self._log_path()

        if not log_path.exists():
            logger.warning('django.log not found at %s; skipping.', log_path)
            self._write_cursor(0)
            return

        cursor = self._read_cursor()
        file_size = log_path.stat().st_size

        if file_size < cursor:
            # Log was rotated — new file is smaller than last cursor position
            logger.info(
                'Log rotation detected (file_size=%d < cursor=%d); resetting cursor.',
                file_size, cursor,
            )
            cursor = 0

        if cursor == file_size:
            return  # nothing new since last run

        with open(log_path, 'rb') as fh:
            fh.seek(cursor)
            raw_bytes = fh.read()
            new_offset = fh.tell()

        docs = []
        for raw_line in raw_bytes.split(b'\n'):
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                doc = json.loads(raw_line)
            except json.JSONDecodeError:
                logger.warning('Skipping non-JSON log line: %r', raw_line[:120])
                continue
            docs.append({
                '_index': 'django-logs',
                '_id': hashlib.sha1(raw_line).hexdigest()[:16],
                '_source': doc,
            })

        if not docs:
            self._write_cursor(new_offset)
            return

        es = Elasticsearch(settings.ELASTICSEARCH_URL, request_timeout=10)
        try:
            success, failed = bulk(es, docs, raise_on_error=False, stats_only=False)
        except (ESConnectionError, Exception) as exc:
            logger.warning(
                'Elasticsearch unavailable (%s); will retry on next run.', exc
            )
            return  # do NOT advance cursor — retry next time

        for item in failed:
            logger.warning('Failed to index document: %s', item)

        logger.info(
            'Forwarded %d log documents to Elasticsearch (index=django-logs). Failed: %d.',
            success, len(failed),
        )
        self._write_cursor(new_offset)
