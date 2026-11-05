// 用法：ocrfind <图片> [词1 词2 ...]   不给词就输出每一行文字和行框。
// 坐标为 0–1、左上原点：[x, y, w, h]。语言：英文、德文、简体中文。
import Foundation
import Vision
let args = CommandLine.arguments
let url = URL(fileURLWithPath: args[1])
let terms = Array(args.dropFirst(2))
let req = VNRecognizeTextRequest()
req.recognitionLevel = .accurate
req.recognitionLanguages = ["en-US", "de-DE", "zh-Hans"]
req.usesLanguageCorrection = false
try VNImageRequestHandler(url: url).perform([req])
var out: [[String: Any]] = []
func box(_ r: CGRect) -> [Double] { [Double(r.minX), Double(1 - r.maxY), Double(r.width), Double(r.height)] }
for ob in req.results ?? [] {
  guard let c = ob.topCandidates(1).first else { continue }
  if terms.isEmpty {
    out.append(["line": c.string, "conf": c.confidence, "box": box(ob.boundingBox)])
  } else {
    for t in terms {
      var start = c.string.startIndex
      while let r = c.string.range(of: t, options: [.caseInsensitive], range: start..<c.string.endIndex) {
        if let b = try? c.boundingBox(for: r) { out.append(["term": t, "line": c.string, "conf": c.confidence, "box": box(b.boundingBox)]) }
        start = r.upperBound
      }
    }
  }
}
let d = try JSONSerialization.data(withJSONObject: out, options: [.prettyPrinted, .sortedKeys])
print(String(data: d, encoding: .utf8)!)
