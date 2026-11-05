import Foundation
import Vision
import CoreImage
import AppKit
// macOS 14+；纯本机 foreground segmentation，输入/输出各一路径。
let input=URL(fileURLWithPath:CommandLine.arguments[1])
let output=URL(fileURLWithPath:CommandLine.arguments[2])
let handler=VNImageRequestHandler(url:input)
let request=VNGenerateForegroundInstanceMaskRequest()
try handler.perform([request])
guard let result=request.results?.first, !result.allInstances.isEmpty else {fatalError("未检测到前景；请提供人工 mask，不能自动宣称抠图成功")}
let buffer=try result.generateMaskedImage(ofInstances:result.allInstances,from:handler,croppedToInstancesExtent:false)
let context=CIContext()
let ci=CIImage(cvPixelBuffer:buffer)
try context.writePNGRepresentation(of:ci,to:output,format:.RGBA8,colorSpace:CGColorSpaceCreateDeviceRGB())
print(output.path)
