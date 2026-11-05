import Foundation
import Vision
import AppKit
let root = CommandLine.arguments[1]
let out = CommandLine.arguments[2]
let fm = FileManager.default
let files = fm.enumerator(atPath: root)!.allObjects.compactMap{$0 as? String}.filter{["jpg","jpeg","png"].contains(($0 as NSString).pathExtension.lowercased())}.sorted()
var results: [[String: Any]] = []
for f in files {
 autoreleasepool {
  let url = URL(fileURLWithPath:root).appendingPathComponent(f)
  let req = VNRecognizeTextRequest()
  req.recognitionLevel = .accurate
  req.recognitionLanguages = ["zh-Hans", "en-US"]
  req.usesLanguageCorrection = false
  do {
   try VNImageRequestHandler(url:url).perform([req])
   let boxes = (req.results ?? []).compactMap { ob -> [String:Any]? in
    guard let c = ob.topCandidates(1).first else {return nil}
    return ["text": c.string, "confidence": c.confidence, "box": [ob.boundingBox.minX,1-ob.boundingBox.maxY,ob.boundingBox.width,ob.boundingBox.height]]
   }
   results.append(["file":f,"status":"success","lines":boxes])
  } catch { results.append(["file":f,"status":"error","error":error.localizedDescription]) }
 }
}
try JSONSerialization.data(withJSONObject: results,options:[.prettyPrinted,.sortedKeys]).write(to:URL(fileURLWithPath:out))
print("OCR pages: \(results.count)")
