"""TEST FIXTURE — not a model answer.

This exists only so the browser tests can exercise the level-unlock path, which is
impossible to test without something that actually clears level 1.

It is deliberately written the way `docs/PLAYBOOK.md` warns against: bare mutable
state, no notion of "as of when", nothing that would survive the level-3 refactor.
Copying it would cost you the assessment, which is rather the point of leaving it
in this shape.
"""


class FileHost:
    def __init__(self):
        self.files = {}

    def file_upload(self, file_name, size):
        if file_name in self.files:
            raise RuntimeError("exists")
        self.files[file_name] = size

    def file_get(self, file_name):
        return self.files.get(file_name)

    def file_copy(self, source, dest):
        if source not in self.files:
            raise RuntimeError("missing")
        self.files[dest] = self.files[source]
