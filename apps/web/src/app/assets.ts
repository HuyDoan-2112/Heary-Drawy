import berry from '../../../../artifact/assets/avatars/berry.svg';
import coco from '../../../../artifact/assets/avatars/coco.svg';
import grape from '../../../../artifact/assets/avatars/grape.svg';
import kiwi from '../../../../artifact/assets/avatars/kiwi.svg';
import lemon from '../../../../artifact/assets/avatars/lemon.svg';
import mango from '../../../../artifact/assets/avatars/mango.svg';
import mint from '../../../../artifact/assets/avatars/mint.svg';
import pepper from '../../../../artifact/assets/avatars/pepper.svg';
import plum from '../../../../artifact/assets/avatars/plum.svg';
import sky from '../../../../artifact/assets/avatars/sky.svg';
import drawyCheer from '../../../../artifact/assets/drawy/drawy-cheer.svg';
import drawyCurious from '../../../../artifact/assets/drawy/drawy-curious.svg';
import drawyListen from '../../../../artifact/assets/drawy/drawy-listen.svg';
import drawyProud from '../../../../artifact/assets/drawy/drawy-proud.svg';
import drawyTalk from '../../../../artifact/assets/drawy/drawy-talk.svg';

import type { AvatarId } from './fixtures';

export const avatarAssets: Record<AvatarId, string> = {
  berry,
  coco,
  grape,
  kiwi,
  lemon,
  mango,
  mint,
  pepper,
  plum,
  sky,
};

export const drawyAssets = {
  cheer: drawyCheer,
  curious: drawyCurious,
  listen: drawyListen,
  proud: drawyProud,
  talk: drawyTalk,
};
