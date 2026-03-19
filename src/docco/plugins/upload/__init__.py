import io

import paramiko

from docco.context import ContentType, Context, Phase
from docco.pipeline import Stage as BaseStage


class Stage(BaseStage):
    name = "upload"
    consumes = ContentType.PDF
    produces = ContentType.PDF
    phase = Phase.POSTPROCESS
    after = ("diffpdf", "dpi")
    valid_config_keys = frozenset(
        {"enable", "host", "port", "user", "password", "path"}
    )

    def process(self, context: Context) -> Context:
        assert isinstance(context.content, bytes)
        cfg = self.get_config(context)
        if not cfg or not cfg.get("enable", True):
            self.log.info("Upload disabled, skipping")
            return context

        for key in ("host", "user", "password", "path"):
            if key not in cfg:
                raise ValueError(f"[upload] missing required config key: {key}")

        host = cfg["host"]
        port = cfg.get("port", 22)
        remote_dir = cfg["path"]
        filename = context.source_path.stem + ".pdf"
        remote_path = f"{remote_dir}/{filename}"

        with paramiko.SSHClient() as ssh:
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, port=port, username=cfg["user"], password=cfg["password"])
            with ssh.open_sftp() as sftp:
                sftp.putfo(io.BytesIO(context.content), remote_path)

        self.log.info("Uploaded %s to %s:%s", filename, host, remote_path)
        return context
