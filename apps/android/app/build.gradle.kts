plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.lonesmartroom.app"
    compileSdk = 35
    buildToolsVersion = "35.0.0"

    defaultConfig {
        applicationId = "com.lonesmartroom.app"
        minSdk = 26
        targetSdk = 35
        versionCode = 14
        versionName = "1.4.0"
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    // Isolate development signing from the existing Android installation.
    // Never install this APK over the Samsung app without verifying its signer.
    signingConfigs {
        getByName("debug") {
            storeFile = rootProject.file("../../.cache/android/debug.keystore")
        }
    }
}
