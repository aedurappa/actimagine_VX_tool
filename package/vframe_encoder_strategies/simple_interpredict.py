import logging

from ..frame_includes import *
from .vframe_encoder_strategy_abstract import VFrameEncoderStrategyAbstract
from .simple_keyframeonly import SimpleKeyframeOnly
from .common import *
from .common.predict_inter import encode_predict_inter_write, block_matching_get_error_dc

logger = logging.getLogger(__name__)
logger.propagate = True


class SimpleInterPredict(SimpleKeyframeOnly):
    """Like SimpleKeyframeOnly (same recursive 16x16->8x8 block split), but for
    8x8 leaf blocks that have a reference frame available (every frame except
    the first), tries motion-compensated inter-prediction FIRST (reusing the
    project's own encode_predict_inter_check/write from
    vframe_encoder_strategies/common/predict_inter.py -- written by the
    original author but never wired into any actual strategy class before
    this). Falls back to the existing DC-intra + residual path when there's
    no reference yet (first frame) or when inter-prediction's residual error
    is too high to be worth it.

    error_threshold: per-pixel MSE cutoff (see encode_predict_inter_check --
    it flags is_worth_encoding=True when error EXCEEDS this, meaning "the
    residual is worth encoding on top of the motion-compensated prediction";
    inter-prediction itself is still used either way once a reference
    exists). 4 is a conservative starting point (allows small quantization-
    level noise between otherwise-identical blocks to skip residual
    entirely); raise it to favor smaller files, lower it to favor fidelity.
    """
    ERROR_THRESHOLD = 100000

    def encode_mb(self, block):
        if block['w'] > block['h']:
            self.writer.unsigned_expgolomb(0)
            self.encode_mb(block_half_left(block))
            self.encode_mb(block_half_right(block))
            if block['w'] == 8 and block['h'] >= 8:
                self.clear_total_coeff(block)
            return

        if block['h'] > 8:
            self.writer.unsigned_expgolomb(2)
            self.encode_mb(block_half_up(block))
            self.encode_mb(block_half_down(block))
            if block['w'] >= 8 and block['h'] == 8:
                self.clear_total_coeff(block)
            return

        # blocks are 8x8 here
        # 2026-10-01: the full four-step motion search (encode_predict_inter_check)
        # made files BIGGER than plain keyframe-only, not smaller -- for this mostly-
        # static source, the motion vectors it finds rarely improve the match enough
        # to pay for their own bit cost. Simpler and actually effective for this kind
        # of content: check ONLY the zero-motion (same x,y) position against the
        # previous frame; if it already matches closely, a DC-only (or DC+small
        # residual) encode is far cheaper than a fresh intra block, with no motion
        # vector overhead at all. Real motion/scene-change blocks fall back to intra.
        if self.vframe.ref_vframes[0] is not None:
            ref_vframe = self.vframe.ref_vframes[0]
            error_dict = {}
            block_matching_get_error_dc(self, ref_vframe, block, error_dict)
            # block_matching_get_error_dc silently no-ops (no 'min_error' key) for
            # blocks flush against the right/bottom edge (its bounds check uses
            # x+w >= width, excluding the legitimately-in-bounds last column/row) --
            # fall through to intra for those rather than KeyError.
            if 'min_error' in error_dict and \
               (error_dict['min_error'] / (block['w'] * block['h'])) <= self.ERROR_THRESHOLD:
                check_result = {
                    'error_dict': error_dict,
                    'min_i': 0,
                    'block': block,
                    'pred_vec': {'x': 0, 'y': 0},
                }
                encode_predict_inter_write(self, check_result)
                return

        # no reference frame yet (first frame) -- same as SimpleKeyframeOnly
        self.predict_dc(block, 'y')
        self.predict_dc(block, 'u')
        self.predict_dc(block, 'v')
        residu_cr = encode_residu_blocks_check(self, block)
        if residu_cr['is_worth_encoding']:
            self.writer.unsigned_expgolomb(22)
            self.writer.unsigned_expgolomb(2)
            self.writer.unsigned_expgolomb(0)
            encode_residu_blocks_write(self, residu_cr)
        else:
            self.writer.unsigned_expgolomb(11)
            self.writer.unsigned_expgolomb(2)
            self.writer.unsigned_expgolomb(0)
