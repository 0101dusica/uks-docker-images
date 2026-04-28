import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, call, patch

from django.core.management import call_command
from django.test import SimpleTestCase

COMMAND = 'analytics.management.commands.forward_logs_to_es'
LOGGER = 'analytics.forward_logs_to_es'

LINE_INFO = json.dumps({
    'asctime': '2026-01-01T00:00:00', 'levelname': 'INFO',
    'name': 'frontend.views', 'message': 'User logged in',
})
LINE_WARN = json.dumps({
    'asctime': '2026-01-01T00:01:00', 'levelname': 'WARNING',
    'name': 'frontend.views', 'message': 'Failed login attempt',
})


def _doc_id(line: str) -> str:
    return hashlib.sha1(line.strip().encode()).hexdigest()[:16]


class ForwardLogsCommandTests(SimpleTestCase):
    """Tests for the forward_logs_to_es management command."""

    def setUp(self):
        self.tmpdir = tempfile.TemporaryDirectory()
        self.log_dir = Path(self.tmpdir.name)
        self.log_file = self.log_dir / 'django.log'
        self.cursor_file = self.log_dir / '.es_cursor'
        self._patch_log_dir = patch('django.conf.settings.LOG_DIR', self.log_dir)
        self._patch_log_dir.start()

    def tearDown(self):
        self._patch_log_dir.stop()
        self.tmpdir.cleanup()

    # ------------------------------------------------------------------ helpers

    def _write_log(self, *lines):
        self.log_file.write_text('\n'.join(lines) + '\n', encoding='utf-8')

    def _set_cursor(self, offset: int):
        self.cursor_file.write_text(str(offset))

    def _cursor(self) -> int:
        return int(self.cursor_file.read_text().strip())

    def _run(self, mock_bulk_return=(2, [])):
        """Run the command with Elasticsearch mocked out. Returns the mock bulk call args."""
        mock_es = MagicMock()
        with patch(f'{COMMAND}.Elasticsearch', return_value=mock_es) as mock_es_cls, \
             patch(f'{COMMAND}.bulk', return_value=mock_bulk_return) as mock_bulk:
            call_command('forward_logs_to_es')
            return mock_es_cls, mock_bulk

    # ------------------------------------------------------------------ normal forwarding

    def test_forwards_all_lines_on_first_run(self):
        # Arrange
        self._write_log(LINE_INFO, LINE_WARN)

        # Act
        _, mock_bulk = self._run()

        # Assert
        self.assertTrue(mock_bulk.called)
        docs = mock_bulk.call_args[0][1]
        self.assertEqual(len(docs), 2)

    def test_forwarded_docs_have_correct_index(self):
        # Arrange
        self._write_log(LINE_INFO)

        # Act
        _, mock_bulk = self._run()

        # Assert
        docs = mock_bulk.call_args[0][1]
        self.assertEqual(docs[0]['_index'], 'django-logs')

    def test_forwarded_docs_have_correct_source(self):
        # Arrange
        self._write_log(LINE_INFO)

        # Act
        _, mock_bulk = self._run()

        # Assert
        docs = mock_bulk.call_args[0][1]
        self.assertEqual(docs[0]['_source']['message'], 'User logged in')
        self.assertEqual(docs[0]['_source']['levelname'], 'INFO')

    def test_forwarded_docs_have_sha1_ids(self):
        # Arrange
        self._write_log(LINE_INFO)

        # Act
        _, mock_bulk = self._run()

        # Assert
        docs = mock_bulk.call_args[0][1]
        expected_id = _doc_id(LINE_INFO)
        self.assertEqual(docs[0]['_id'], expected_id)

    def test_cursor_advanced_to_end_of_file_after_success(self):
        # Arrange
        self._write_log(LINE_INFO, LINE_WARN)
        expected_offset = self.log_file.stat().st_size

        # Act
        self._run()

        # Assert
        self.assertEqual(self._cursor(), expected_offset)

    def test_command_logs_forwarded_count(self):
        # Arrange
        self._write_log(LINE_INFO, LINE_WARN)

        # Act
        with patch(f'{COMMAND}.Elasticsearch', return_value=MagicMock()), \
             patch(f'{COMMAND}.bulk', return_value=(2, [])), \
             self.assertLogs(LOGGER, level='INFO') as cm:
            call_command('forward_logs_to_es')

        # Assert
        self.assertTrue(any('Forwarded 2' in msg for msg in cm.output))

    # ------------------------------------------------------------------ incremental reads

    def test_does_not_reindex_already_forwarded_lines(self):
        # Arrange — first run forwards LINE_INFO
        self._write_log(LINE_INFO)
        self._run()
        cursor_after_first = self._cursor()

        # Arrange — append a new line
        with open(self.log_file, 'a', encoding='utf-8') as fh:
            fh.write(LINE_WARN + '\n')

        # Act — second run
        _, mock_bulk = self._run()

        # Assert — only LINE_WARN is indexed on the second run
        docs = mock_bulk.call_args[0][1]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['_source']['message'], 'Failed login attempt')

    def test_nothing_indexed_when_no_new_lines(self):
        # Arrange — cursor already at end of file
        self._write_log(LINE_INFO)
        self._set_cursor(self.log_file.stat().st_size)

        # Act
        _, mock_bulk = self._run()

        # Assert
        self.assertFalse(mock_bulk.called)

    # ------------------------------------------------------------------ log file missing

    def test_missing_log_file_does_not_raise(self):
        # Arrange — log file does not exist
        # Act / Assert — should not raise
        self._run()

    def test_missing_log_file_writes_zero_cursor(self):
        # Arrange
        # Act
        self._run()

        # Assert
        self.assertEqual(self._cursor(), 0)

    def test_missing_log_file_emits_warning(self):
        # Arrange / Act
        with patch(f'{COMMAND}.Elasticsearch', return_value=MagicMock()), \
             patch(f'{COMMAND}.bulk'), \
             self.assertLogs(LOGGER, level='WARNING') as cm:
            call_command('forward_logs_to_es')

        # Assert
        self.assertTrue(any('not found' in msg for msg in cm.output))

    # ------------------------------------------------------------------ log rotation

    def test_cursor_reset_when_log_rotation_detected(self):
        # Arrange — cursor is larger than the (new, short) log file
        self._write_log(LINE_INFO)
        large_fake_cursor = self.log_file.stat().st_size + 9999
        self._set_cursor(large_fake_cursor)

        # Act
        self._run()

        # Assert — cursor reset and both lines forwarded from byte 0
        self.assertGreater(self._cursor(), 0)
        self.assertLessEqual(self._cursor(), self.log_file.stat().st_size)

    def test_rotation_detection_logs_info(self):
        # Arrange
        self._write_log(LINE_INFO)
        self._set_cursor(self.log_file.stat().st_size + 9999)

        # Act
        with patch(f'{COMMAND}.Elasticsearch', return_value=MagicMock()), \
             patch(f'{COMMAND}.bulk', return_value=(1, [])), \
             self.assertLogs(LOGGER, level='INFO') as cm:
            call_command('forward_logs_to_es')

        # Assert
        self.assertTrue(any('rotation' in msg.lower() for msg in cm.output))

    # ------------------------------------------------------------------ ES unavailable

    def test_cursor_not_advanced_when_es_unavailable(self):
        # Arrange
        self._write_log(LINE_INFO)
        self._set_cursor(0)
        from elasticsearch import ConnectionError as ESConnectionError

        # Act
        with patch(f'{COMMAND}.Elasticsearch', return_value=MagicMock()), \
             patch(f'{COMMAND}.bulk', side_effect=ESConnectionError('refused')):
            call_command('forward_logs_to_es')

        # Assert — cursor stays at 0
        self.assertEqual(self._cursor(), 0)

    def test_es_unavailable_emits_warning(self):
        # Arrange
        self._write_log(LINE_INFO)
        from elasticsearch import ConnectionError as ESConnectionError

        # Act
        with patch(f'{COMMAND}.Elasticsearch', return_value=MagicMock()), \
             patch(f'{COMMAND}.bulk', side_effect=ESConnectionError('refused')), \
             self.assertLogs(LOGGER, level='WARNING') as cm:
            call_command('forward_logs_to_es')

        # Assert
        self.assertTrue(any('unavailable' in msg.lower() for msg in cm.output))

    # ------------------------------------------------------------------ malformed JSON

    def test_malformed_json_line_is_skipped(self):
        # Arrange
        self._write_log('not valid json', LINE_INFO)

        # Act
        _, mock_bulk = self._run()

        # Assert — only LINE_INFO is indexed
        docs = mock_bulk.call_args[0][1]
        self.assertEqual(len(docs), 1)
        self.assertEqual(docs[0]['_source']['message'], 'User logged in')

    def test_malformed_json_line_emits_warning(self):
        # Arrange
        self._write_log('not valid json', LINE_INFO)

        # Act
        with patch(f'{COMMAND}.Elasticsearch', return_value=MagicMock()), \
             patch(f'{COMMAND}.bulk', return_value=(1, [])), \
             self.assertLogs(LOGGER, level='WARNING') as cm:
            call_command('forward_logs_to_es')

        # Assert
        self.assertTrue(any('non-JSON' in msg for msg in cm.output))

    # ------------------------------------------------------------------ idempotency

    def test_same_line_produces_same_doc_id(self):
        # Arrange
        self._write_log(LINE_INFO)

        # Act — run twice (reset cursor each time to re-read)
        _, mock_bulk_1 = self._run()
        self._set_cursor(0)
        _, mock_bulk_2 = self._run()

        # Assert — doc IDs are identical
        id_1 = mock_bulk_1.call_args[0][1][0]['_id']
        id_2 = mock_bulk_2.call_args[0][1][0]['_id']
        self.assertEqual(id_1, id_2)

    # ------------------------------------------------------------------ empty lines

    def test_empty_lines_are_not_indexed(self):
        # Arrange — file with blank lines between log entries
        self.log_file.write_text(
            f'\n{LINE_INFO}\n\n{LINE_WARN}\n\n', encoding='utf-8'
        )

        # Act
        _, mock_bulk = self._run()

        # Assert — only the two valid lines
        docs = mock_bulk.call_args[0][1]
        self.assertEqual(len(docs), 2)
