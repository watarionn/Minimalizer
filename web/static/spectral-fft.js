(function (root, factory) {
  const api = factory();
  if (typeof module !== "undefined" && module.exports) module.exports = api;
  if (root) root.MinimalizerSpectralFFT = api;
})(typeof globalThis !== "undefined" ? globalThis : this, function () {
  "use strict";

  function isPowerOfTwo(value) {
    return value > 0 && (value & (value - 1)) === 0;
  }

  function nextPowerOfTwo(value) {
    let size = 1;
    while (size < value) size <<= 1;
    return size;
  }

  function fftRadix2(real, imag, inverse) {
    const n = real.length;
    if (imag.length !== n) throw new Error("FFT real/imag length mismatch.");
    if (!isPowerOfTwo(n)) throw new Error("radix-2 FFT requires power-of-two length.");

    let j = 0;
    for (let i = 1; i < n; i += 1) {
      let bit = n >> 1;
      while (j & bit) {
        j ^= bit;
        bit >>= 1;
      }
      j ^= bit;
      if (i < j) {
        const tr = real[i];
        real[i] = real[j];
        real[j] = tr;
        const ti = imag[i];
        imag[i] = imag[j];
        imag[j] = ti;
      }
    }

    const sign = inverse ? 1 : -1;
    for (let length = 2; length <= n; length <<= 1) {
      const angle = sign * 2 * Math.PI / length;
      const wlenR = Math.cos(angle);
      const wlenI = Math.sin(angle);
      const half = length >> 1;
      for (let base = 0; base < n; base += length) {
        let wr = 1;
        let wi = 0;
        for (let offset = 0; offset < half; offset += 1) {
          const even = base + offset;
          const odd = even + half;
          const or = real[odd] * wr - imag[odd] * wi;
          const oi = real[odd] * wi + imag[odd] * wr;
          const er = real[even];
          const ei = imag[even];
          real[even] = er + or;
          imag[even] = ei + oi;
          real[odd] = er - or;
          imag[odd] = ei - oi;
          const nextWr = wr * wlenR - wi * wlenI;
          wi = wr * wlenI + wi * wlenR;
          wr = nextWr;
        }
      }
    }

    if (inverse) {
      const scale = 1 / n;
      for (let i = 0; i < n; i += 1) {
        real[i] *= scale;
        imag[i] *= scale;
      }
    }
  }

  function fftBluesteinForward(real, imag) {
    const n = real.length;
    const m = nextPowerOfTwo(2 * n - 1);
    const ar = new Float64Array(m);
    const ai = new Float64Array(m);
    const br = new Float64Array(m);
    const bi = new Float64Array(m);

    for (let i = 0; i < n; i += 1) {
      const angle = Math.PI * ((i * i) % (2 * n)) / n;
      const c = Math.cos(angle);
      const s = Math.sin(angle);
      ar[i] = real[i] * c + imag[i] * s;
      ai[i] = imag[i] * c - real[i] * s;
      br[i] = c;
      bi[i] = s;
      if (i !== 0) {
        br[m - i] = c;
        bi[m - i] = s;
      }
    }

    fftRadix2(ar, ai, false);
    fftRadix2(br, bi, false);
    for (let i = 0; i < m; i += 1) {
      const rr = ar[i] * br[i] - ai[i] * bi[i];
      const ii = ar[i] * bi[i] + ai[i] * br[i];
      ar[i] = rr;
      ai[i] = ii;
    }
    fftRadix2(ar, ai, true);

    for (let i = 0; i < n; i += 1) {
      const angle = Math.PI * ((i * i) % (2 * n)) / n;
      const c = Math.cos(angle);
      const s = Math.sin(angle);
      const rr = ar[i] * c + ai[i] * s;
      const ii = ai[i] * c - ar[i] * s;
      real[i] = rr;
      imag[i] = ii;
    }
  }

  function fftAny(real, imag, inverse) {
    if (real.length !== imag.length) throw new Error("FFT real/imag length mismatch.");
    const n = real.length;
    if (n === 0) return;
    if (n === 1) return;
    if (inverse) {
      for (let i = 0; i < n; i += 1) imag[i] = -imag[i];
      fftAny(real, imag, false);
      const scale = 1 / n;
      for (let i = 0; i < n; i += 1) {
        real[i] *= scale;
        imag[i] = -imag[i] * scale;
      }
      return;
    }
    if (isPowerOfTwo(n)) {
      fftRadix2(real, imag, false);
    } else {
      fftBluesteinForward(real, imag);
    }
  }

  function fft2(real, imag, width, height, inverse) {
    const count = width * height;
    if (real.length !== count || imag.length !== count) {
      throw new Error("FFT2 buffer size mismatch.");
    }

    const rowR = new Float64Array(width);
    const rowI = new Float64Array(width);
    for (let y = 0; y < height; y += 1) {
      const base = y * width;
      for (let x = 0; x < width; x += 1) {
        rowR[x] = real[base + x];
        rowI[x] = imag[base + x];
      }
      fftAny(rowR, rowI, inverse);
      for (let x = 0; x < width; x += 1) {
        real[base + x] = rowR[x];
        imag[base + x] = rowI[x];
      }
    }

    const colR = new Float64Array(height);
    const colI = new Float64Array(height);
    for (let x = 0; x < width; x += 1) {
      for (let y = 0; y < height; y += 1) {
        const index = y * width + x;
        colR[y] = real[index];
        colI[y] = imag[index];
      }
      fftAny(colR, colI, inverse);
      for (let y = 0; y < height; y += 1) {
        const index = y * width + x;
        real[index] = colR[y];
        imag[index] = colI[y];
      }
    }
  }

  function exactL0StructuralRgba(rgba, width, height, options) {
    const config = Object.assign({
      lambda: 0.010,
      kappa: 2.0,
      betaMax: 1.0e5,
    }, options || {});
    const count = width * height;
    const source = [
      new Float64Array(count),
      new Float64Array(count),
      new Float64Array(count),
    ];
    for (let i = 0; i < count; i += 1) {
      const o = i * 4;
      source[0][i] = rgba[o] / 255;
      source[1][i] = rgba[o + 1] / 255;
      source[2][i] = rgba[o + 2] / 255;
    }

    const sourceFftR = [];
    const sourceFftI = [];
    for (let channel = 0; channel < 3; channel += 1) {
      const re = new Float64Array(source[channel]);
      const im = new Float64Array(count);
      fft2(re, im, width, height, false);
      sourceFftR.push(re);
      sourceFftI.push(im);
    }

    const denominator = new Float64Array(count);
    for (let y = 0; y < height; y += 1) {
      const fy = y / Math.max(height, 1);
      const dy = 4 * Math.sin(Math.PI * fy) ** 2;
      for (let x = 0; x < width; x += 1) {
        const fx = x / Math.max(width, 1);
        denominator[y * width + x] = dy + 4 * Math.sin(Math.PI * fx) ** 2;
      }
    }

    const result = source.map((channel) => new Float64Array(channel));
    const h = source.map(() => new Float64Array(count));
    const v = source.map(() => new Float64Array(count));
    const divergence = source.map(() => new Float64Array(count));
    let beta = 2 * config.lambda;

    while (beta < config.betaMax) {
      const threshold = config.lambda / beta;
      for (let y = 0; y < height; y += 1) {
        const down = y + 1 < height ? y + 1 : 0;
        for (let x = 0; x < width; x += 1) {
          const right = x + 1 < width ? x + 1 : 0;
          const index = y * width + x;
          const rightIndex = y * width + right;
          const downIndex = down * width + x;
          let energy = 0;
          for (let channel = 0; channel < 3; channel += 1) {
            const hd = result[channel][rightIndex] - result[channel][index];
            const vd = result[channel][downIndex] - result[channel][index];
            h[channel][index] = hd;
            v[channel][index] = vd;
            energy += hd * hd + vd * vd;
          }
          if (energy < threshold) {
            for (let channel = 0; channel < 3; channel += 1) {
              h[channel][index] = 0;
              v[channel][index] = 0;
            }
          }
        }
      }

      for (let y = 0; y < height; y += 1) {
        const up = y > 0 ? y - 1 : height - 1;
        for (let x = 0; x < width; x += 1) {
          const left = x > 0 ? x - 1 : width - 1;
          const index = y * width + x;
          const leftIndex = y * width + left;
          const upIndex = up * width + x;
          for (let channel = 0; channel < 3; channel += 1) {
            divergence[channel][index] = (
              h[channel][leftIndex] - h[channel][index]
              + v[channel][upIndex] - v[channel][index]
            );
          }
        }
      }

      for (let channel = 0; channel < 3; channel += 1) {
        const divR = new Float64Array(divergence[channel]);
        const divI = new Float64Array(count);
        fft2(divR, divI, width, height, false);
        for (let i = 0; i < count; i += 1) {
          const scale = 1 / (1 + beta * denominator[i]);
          divR[i] = (sourceFftR[channel][i] + beta * divR[i]) * scale;
          divI[i] = (sourceFftI[channel][i] + beta * divI[i]) * scale;
        }
        fft2(divR, divI, width, height, true);
        result[channel] = divR;
      }
      beta *= config.kappa;
    }

    const output = new Uint8ClampedArray(count * 4);
    for (let i = 0; i < count; i += 1) {
      const o = i * 4;
      for (let channel = 0; channel < 3; channel += 1) {
        output[o + channel] = Math.round(Math.min(1, Math.max(0, result[channel][i])) * 255);
      }
      output[o + 3] = rgba[o + 3];
    }
    return output;
  }

  return {
    isPowerOfTwo,
    nextPowerOfTwo,
    fftRadix2,
    fftAny,
    fft2,
    exactL0StructuralRgba,
  };
});
