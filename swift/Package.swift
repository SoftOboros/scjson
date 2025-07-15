// swift-tools-version: 5.9
import PackageDescription

let package = Package(
    name: "scjson-swift",
    products: [
        .executable(name: "scjson-swift", targets: ["scjson"])
    ],
    dependencies: [
        .package(url: "https://github.com/apple/swift-argument-parser", from: "1.2.2")
    ],
    targets: [
        .executableTarget(
            name: "scjson",
            dependencies: [
                .product(name: "ArgumentParser", package: "swift-argument-parser")
            ]
        ),
        .testTarget(
            name: "scjsonTests",
            dependencies: ["scjson"]
        )
    ]
)
