import { describe, expect, it } from 'vitest';
import type { RoleFilteredSnapshot } from '../../generated/contracts';
import drawerCollaborating from '../../../../../contracts/fixtures/drawer-collaborating.snapshot.json';
import speakerCollaborating from '../../../../../contracts/fixtures/speaker-collaborating.snapshot.json';

const secretFieldNames = [
  'object_id',
  'display_name',
  'image_url',
  'model_url',
  'rubric',
  'asset_url',
  'model_bytes',
];

describe('contract fixtures', () => {
  it('can be consumed through generated frontend types', () => {
    const speaker = speakerCollaborating as unknown as RoleFilteredSnapshot;
    const drawer = drawerCollaborating as unknown as RoleFilteredSnapshot;

    expect(speaker.round.role).toBe('speaker');
    expect(speaker.object_access?.object_id).toBe('object-demo-speaker-only');
    expect(drawer.round.role).toBe('drawer');
  });

  it('keeps Drawer-before-Reveal fixtures secret blind', () => {
    const serialized = JSON.stringify(drawerCollaborating);

    expect('object_access' in drawerCollaborating).toBe(false);
    for (const field of secretFieldNames) {
      expect(serialized).not.toContain(field);
    }
  });
});
