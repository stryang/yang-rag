const STORAGE_KEY = 'theme-color'

export const DEFAULT_THEME_COLOR = '#4a8b6b'

export const THEME_PRESETS = [
  { name: '森林绿', hex: '#4a8b6b' },
  { name: '海洋蓝', hex: '#3b82f6' },
  { name: '靛蓝', hex: '#6366f1' },
  { name: '紫罗兰', hex: '#8b5cf6' },
  { name: '玫瑰红', hex: '#e11d48' },
  { name: '琥珀橙', hex: '#d97706' },
  { name: '青碧', hex: '#0d9488' },
  { name: '岩灰', hex: '#64748b' },
  { name: '翠绿', hex: '#04d16a' },
]

function hexToRgb(hex: string): [number, number, number] {
  const cleaned = hex.replace('#', '')
  const r = parseInt(cleaned.slice(0, 2), 16)
  const g = parseInt(cleaned.slice(2, 4), 16)
  const b = parseInt(cleaned.slice(4, 6), 16)
  return [r, g, b]
}

function rgbToHsl(r: number, g: number, b: number): [number, number, number] {
  r /= 255
  g /= 255
  b /= 255

  const max = Math.max(r, g, b)
  const min = Math.min(r, g, b)
  const l = (max + min) / 2

  if (max === min) {
    return [0, 0, l * 100]
  }

  const d = max - min
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min)

  let h = 0
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6
  else if (max === g) h = ((b - r) / d + 2) / 6
  else h = ((r - g) / d + 4) / 6

  return [h * 360, s * 100, l * 100]
}

function hslToRgb(h: number, s: number, l: number): [number, number, number] {
  h /= 360
  s /= 100
  l /= 100

  if (s === 0) {
    const val = Math.round(l * 255)
    return [val, val, val]
  }

  const hue2rgb = (p: number, q: number, t: number) => {
    if (t < 0) t += 1
    if (t > 1) t -= 1
    if (t < 1 / 6) return p + (q - p) * 6 * t
    if (t < 1 / 2) return q
    if (t < 2 / 3) return p + (q - p) * (2 / 3 - t) * 6
    return p
  }

  const q = l < 0.5 ? l * (1 + s) : l + s - l * s
  const p = 2 * l - q

  return [
    Math.round(hue2rgb(p, q, h + 1 / 3) * 255),
    Math.round(hue2rgb(p, q, h) * 255),
    Math.round(hue2rgb(p, q, h - 1 / 3) * 255),
  ]
}

interface ShadeConfig {
  shade: number
  lightness: number
  saturationScale: number
}

const SHADE_MAP: ShadeConfig[] = [
  { shade: 50,  lightness: 91, saturationScale: 0.55 },
  { shade: 100, lightness: 85, saturationScale: 0.60 },
  { shade: 200, lightness: 78, saturationScale: 0.65 },
  { shade: 300, lightness: 72, saturationScale: 0.70 },
  { shade: 400, lightness: 58, saturationScale: 0.85 },
  { shade: 500, lightness: -1, saturationScale: 1.00 },
  { shade: 600, lightness: -1, saturationScale: 1.05 },
  { shade: 700, lightness: -1, saturationScale: 1.00 },
  { shade: 800, lightness: -1, saturationScale: 0.95 },
  { shade: 900, lightness: -1, saturationScale: 0.90 },
  { shade: 950, lightness: -1, saturationScale: 0.80 },
]

export function generatePalette(hex: string): Record<string, string> {
  const [r, g, b] = hexToRgb(hex)
  const [h, s, l] = rgbToHsl(r, g, b)

  const result: Record<string, string> = {}

  for (const config of SHADE_MAP) {
    const newS = Math.min(Math.max(s * config.saturationScale, 5), 100)
    let newL: number

    if (config.shade === 500) {
      newL = l
    } else if (config.shade < 500) {
      newL = config.lightness
    } else {
      const darkenSteps: Record<number, number> = {
        600: 9, 700: 15, 800: 20, 900: 24, 950: 32,
      }
      newL = Math.max(l - darkenSteps[config.shade], 4)
    }

    newL = Math.min(Math.max(newL, 3), 98)

    const [cr, cg, cb] = hslToRgb(h, newS, newL)
    result[String(config.shade)] = `${cr} ${cg} ${cb}`
  }

  return result
}

export function applyTheme(hex: string): void {
  const palette = generatePalette(hex)
  const root = document.documentElement

  for (const [shade, channels] of Object.entries(palette)) {
    root.style.setProperty(`--primary-${shade}`, channels)
  }

  try {
    localStorage.setItem(STORAGE_KEY, hex)
  } catch {
    // localStorage unavailable
  }
}

export function getStoredThemeColor(): string | null {
  try {
    return localStorage.getItem(STORAGE_KEY)
  } catch {
    return null
  }
}

export function initializeTheme(): void {
  const stored = getStoredThemeColor()
  applyTheme(stored || DEFAULT_THEME_COLOR)
}

export function isValidHex(value: string): boolean {
  return /^#[0-9a-fA-F]{6}$/.test(value)
}
