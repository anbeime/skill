import Foundation
import Vision
import AppKit
let items=try JSONSerialization.jsonObject(with:Data(contentsOf:URL(fileURLWithPath:CommandLine.arguments[1]))) as! [String]
var result:[[String:Any]]=[]
for path in items {
 do {
  let request=VNDetectFaceRectanglesRequest();try VNImageRequestHandler(url:URL(fileURLWithPath:path)).perform([request])
  let faces=(request.results ?? []).map { face -> [Double] in let b=face.boundingBox;return [Double(b.minX),Double(1-b.maxY),Double(b.width),Double(b.height)] }
  result.append(["path":path,"faces":faces,"detector":"macOS Vision VNDetectFaceRectanglesRequest","status":"success"])
 } catch {result.append(["path":path,"faces":[],"status":"error","error":String(describing:error)])}
}
let out=try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys]);try out.write(to:URL(fileURLWithPath:CommandLine.arguments[2]));print("Face audit: \(result.count) images")
