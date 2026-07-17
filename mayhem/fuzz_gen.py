#!/usr/bin/env python3
"""Atheris fuzz harness for python-qrcode (target: make-fuzz).

Ported from the original mayhemheroes integration (mayhem/fuzz_gen.py on the
archived branch): exercises qrcode.make() end-to-end on arbitrary input.
Atheris instruments the imported qrcode modules so libFuzzer gets coverage
feedback while the encoder (data analysis, segment packing, Reed-Solomon
error correction, matrix masking) and the renderers run on fuzzed data.

There is deliberately no in-harness timer: a slow or hanging input is
reported by the runner -- libFuzzer's own -timeout / Mayhem's per-test timeout --
instead of being silently swallowed. The only bound is the deterministic
payload-size cap below (_MAX_PAYLOAD), which counts bytes, not time.

Run modes (driven by the compiled launcher `qrcode_fuzzer` / `-standalone`):
  * fuzzing      -- `python3 fuzz_gen.py [libFuzzer args]`
  * single input -- `python3 fuzz_gen.py <file>` (libFuzzer runs it once)
"""
import io
import logging
import sys

import atheris

with atheris.instrument_imports():
    import qrcode
    import qrcode.image.pil
    import qrcode.image.svg
    from qrcode.exceptions import DataOverflowError

logging.disable(logging.CRITICAL)


# QR version 40 binary capacity is ~2953 bytes; anything longer only raises
# DataOverflowError, so cap the payload to keep every input productive.
_MAX_PAYLOAD = 3000


@atheris.instrument_func
def TestOneInput(data):
    payload = data[:_MAX_PAYLOAD]
    try:
        # The original harness's code path: full pipeline into a PIL image.
        qrcode.make(payload)

        # Drive the explicit QRCode API + the pure-python SVG renderer too.
        qr = qrcode.QRCode(error_correction=qrcode.constants.ERROR_CORRECT_L)
        qr.add_data(payload)
        qr.make(fit=True)
        qr.get_matrix()
        img = qr.make_image(image_factory=qrcode.image.svg.SvgPathImage)
        img.save(io.BytesIO())
    except DataOverflowError:
        # Expected for payloads that exceed QR capacity.
        pass


def main():
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()


if __name__ == "__main__":
    main()
