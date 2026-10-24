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
        versionCode = 18
        versionName = "2.0.0-dev.4"
    }

    buildFeatures { buildConfig = true }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlinOptions { jvmTarget = "17" }

    // Ordinary builds stay isolated. The opt-in local build uses the original
    // debug keystore in place, with AGP's in-memory debug signing defaults.
    // No passwords or private signing files belong in this repository.
    signingConfigs {
        getByName("debug") {
            val original = providers.environmentVariable("LONE_ANDROID_SIGNING_KEYSTORE").orNull
            storeFile = if (original == null) {
                rootProject.file("../../.cache/android/debug.keystore")
            } else {
                file(original).also { require(it.isFile) { "Original signing keystore is unavailable" } }
            }
        }
    }
}
