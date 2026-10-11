// Approved artwork from artifact/assets is inlined (not loaded through <img>) because several
// poses intentionally draw outside their viewBox (wings, stems), which an <img> would clip.
import berry from '../../../../artifact/assets/avatars/berry.svg?raw';
import coco from '../../../../artifact/assets/avatars/coco.svg?raw';
import grape from '../../../../artifact/assets/avatars/grape.svg?raw';
import kiwi from '../../../../artifact/assets/avatars/kiwi.svg?raw';
import lemon from '../../../../artifact/assets/avatars/lemon.svg?raw';
import mango from '../../../../artifact/assets/avatars/mango.svg?raw';
import mint from '../../../../artifact/assets/avatars/mint.svg?raw';
import pepper from '../../../../artifact/assets/avatars/pepper.svg?raw';
import plum from '../../../../artifact/assets/avatars/plum.svg?raw';
import sky from '../../../../artifact/assets/avatars/sky.svg?raw';
import drawyCheer from '../../../../artifact/assets/drawy/drawy-cheer.svg?raw';
import drawyListen from '../../../../artifact/assets/drawy/drawy-listen.svg?raw';
import drawyProud from '../../../../artifact/assets/drawy/drawy-proud.svg?raw';
import drawySearch from '../../../../artifact/assets/drawy/drawy-search.svg?raw';
import drawyTalk from '../../../../artifact/assets/drawy/drawy-talk.svg?raw';
// Mirrored curious pose with the question mark kept readable, extracted verbatim from artifact/design/Main.dc.html.
import drawyCuriousMirrored from './assets/drawy-curious-mirrored.svg?raw';

import type { AvatarId } from './fixtures';

/** Drops the fixed size and accessible name so the caller decides both. */
function artwork(svg: string): string {
  return svg
    .replace(/ width="\d+" height="\d+"/, ' width="100%" height="100%"')
    .replace(/ role="img" aria-label="[^"]*"/, ' aria-hidden="true" focusable="false"');
}

export const avatarAssets: Record<AvatarId, string> = {
  berry: artwork(berry),
  coco: artwork(coco),
  grape: artwork(grape),
  kiwi: artwork(kiwi),
  lemon: artwork(lemon),
  mango: artwork(mango),
  mint: artwork(mint),
  pepper: artwork(pepper),
  plum: artwork(plum),
  sky: artwork(sky),
};

export const drawyAssets = {
  cheer: artwork(drawyCheer),
  curiousMirrored: artwork(drawyCuriousMirrored),
  listen: artwork(drawyListen),
  proud: artwork(drawyProud),
  search: artwork(drawySearch),
  talk: artwork(drawyTalk),
};

export type DrawyPose = keyof typeof drawyAssets;

export function isAvatarId(value: string): value is AvatarId {
  return Object.hasOwn(avatarAssets, value);
}
