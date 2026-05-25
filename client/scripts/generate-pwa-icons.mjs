import { readFile } from "node:fs/promises"
import { fileURLToPath } from "node:url"
import { dirname, resolve } from "node:path"
import sharp from "sharp"

const __dirname = dirname(fileURLToPath(import.meta.url))
const publicDir = resolve(__dirname, "..", "public")

const svgSource = await readFile(resolve(publicDir, "icon.svg"), "utf8")

// Reemplaza el bloque <style> con fills hardcoded para que el render
// no dependa de prefers-color-scheme (sharp no lo aplica).
const svgForRaster = svgSource
  .replace(/<style>[\s\S]*?<\/style>/, "")
  .replaceAll('class="background"', 'fill="#171717"')
  .replaceAll('class="foreground"', 'fill="#ffffff"')

for (const size of [192, 512]) {
  const out = resolve(publicDir, `icon-${size}.png`)
  await sharp(Buffer.from(svgForRaster))
    .resize(size, size)
    .png()
    .toFile(out)
  console.log(`wrote ${out}`)
}
