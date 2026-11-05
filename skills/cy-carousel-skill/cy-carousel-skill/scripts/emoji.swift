// 用法：emoji <文字> <输出.png> <字号pt>
// 用 AppKit（Apple Color Emoji）把 emoji 渲染成透明 PNG，组合序列（1️⃣ 2️⃣ 👉🏻 ⚠️ 🇨🇳）也能正确合成。
// 1pt = 1px；四周留透明边，调用方（手排.py 的 emoji()）按墨迹裁边。首次由 手排.emoji() 自动编译到 bin/emoji。
import AppKit

let args = CommandLine.arguments
guard args.count >= 4, let pt = Double(args[3]), pt > 0 else {
  FileHandle.standardError.write("用法：emoji <文字> <输出.png> <字号pt>\n".data(using: .utf8)!)
  exit(2)
}
let text = args[1], out = args[2]
let font = NSFont(name: "Apple Color Emoji", size: CGFloat(pt)) ?? NSFont.systemFont(ofSize: CGFloat(pt))
let attr = NSAttributedString(string: text, attributes: [.font: font])
let sz = attr.size()
let pad = CGFloat(pt) * 0.25
let w = Int(ceil(sz.width + 2 * pad)), h = Int(ceil(sz.height + 2 * pad))
guard let rep = NSBitmapImageRep(bitmapDataPlanes: nil, pixelsWide: w, pixelsHigh: h, bitsPerSample: 8,
                                 samplesPerPixel: 4, hasAlpha: true, isPlanar: false, colorSpaceName: .deviceRGB,
                                 bytesPerRow: 0, bitsPerPixel: 0) else { exit(1) }
rep.size = NSSize(width: w, height: h)
NSGraphicsContext.saveGraphicsState()
NSGraphicsContext.current = NSGraphicsContext(bitmapImageRep: rep)
attr.draw(at: NSPoint(x: pad, y: pad))
NSGraphicsContext.restoreGraphicsState()
guard let png = rep.representation(using: .png, properties: [:]) else { exit(1) }
do { try png.write(to: URL(fileURLWithPath: out)) } catch { FileHandle.standardError.write("\(error)\n".data(using: .utf8)!); exit(1) }
