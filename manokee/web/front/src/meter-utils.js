export function factor_to_dB(factor) {
  return 20.0 * Math.log10(factor);
}

export function dB_to_factor(dB) {
  return Math.pow(10, dB / 20.0);
}

export function gains_for_track(track, meter_value) {
  const factor = dB_to_factor(meter_value);
  return [factor * (1.0 - track.pan), factor * (1.0 + track.pan)];
}

export function calculate_tracks_audibility(tracks, is_transport_rolling) {
  const soloed = tracks.some((track) => track.is_solo);
  return tracks.reduce((result, track) => {
    if (is_transport_rolling)
      result[track.name] = soloed ? track.is_solo : !track.is_mute;
    else result[track.name] = false;
    return result;
  }, {});
}
