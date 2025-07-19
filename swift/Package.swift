// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "scjson-swift",
    products: [
        .library(name: "SCJSONKit", targets: ["SCJSONKit"]),
        .executable(name: "scjson-swift", targets: ["scjson"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.2.2")
    ],
    targets: [
        .target(
            name: "SCJSONKit",
            dependencies: []
        ),
        .executableTarget(
            name: "scjson",
            dependencies: [
                "SCJSONKit",
                .product(name: "ArgumentParser", package: "swift-argument-parser")
            ]
        ),
        .testTarget(
            name: "scjsonTests",
            dependencies: ["scjson"]
        )
    ]
)
