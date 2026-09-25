import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import vm from 'node:vm';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const html = readFileSync(join(root, 'index.html'), 'utf8');
const programRows = readFileSync(join(root, 'data/all_msgis_institutions_2026.csv'), 'utf8').trimEnd().split(/\r?\n/);
const coordinateRows = readFileSync(join(root, 'data/universities_coordinates_2026.csv'), 'utf8').trimEnd().split(/\r?\n/);
const trackRows = readFileSync(join(root, 'data/program_tracks_2026.csv'), 'utf8').trimEnd().split(/\r?\n/);

assert.equal(programRows.length - 1, 174);
assert.equal(coordinateRows.length - 1, 140);
assert.equal(trackRows.length - 1, 3);
for (const filename of ['all_msgis_institutions_2026.csv', 'universities_coordinates_2026.csv', 'program_tracks_2026.csv']) {
    assert.ok(html.includes(`data/${filename}`), `${filename} is not loaded by the website`);
}

const tracks = trackRows.slice(1).map(line => {
    const [Institution, Program, Track, link] = line.split(',');
    return { Institution, Program, Track, link };
});
const start = html.indexOf('function escapeHtml(value)');
const end = html.indexOf('// Simple CSV export functionality', start);
assert.ok(start !== -1 && end > start);
const popupFunctions = html.slice(start, end);
const data = {
    institution: 'Liberty University',
    state: 'VA',
    city: 'Lynchburg',
    programs: [{
        name: 'MS Geographic Information Systems',
        link: 'https://catalog.liberty.edu/graduate/colleges-schools/arts-sciences/geographic-information-systems-ms/',
        type: 'professional',
        location: 'online',
        duration: '36 cr',
        graduation: 'non-thesis',
        tracks,
    }],
};
const popup = vm.runInNewContext(`${popupFunctions}\ncreatePopupContent(data)`, {
    data,
    colorMap: { professional: '#56B4E9', default: '#ffaa00' },
});
for (const track of tracks) {
    assert.ok(popup.includes(track.Track.replace('&', '&amp;')), `${track.Track} is missing from popup`);
    assert.ok(popup.includes(track.link), `${track.Track} link is missing from popup`);
}
assert.ok(popup.includes('Total Programs:</strong> 1'));
console.log('2026 data paths, counts, and Liberty track popup: OK');
