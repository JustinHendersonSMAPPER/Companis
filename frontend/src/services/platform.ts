/**
 * Platform detection utilities for Capacitor hybrid app.
 * Provides fallbacks when running in browser for development.
 */

let _isNative: boolean | null = null;

export function isNativePlatform(): boolean {
  if (_isNative !== null) return _isNative;
  try {
    // Capacitor sets this on the window object when running natively
    const win = window as unknown as { Capacitor?: { isNativePlatform: () => boolean } };
    _isNative = win.Capacitor?.isNativePlatform() ?? false;
  } catch {
    _isNative = false;
  }
  return _isNative;
}

export function getPlatform(): "android" | "ios" | "web" {
  try {
    const win = window as unknown as { Capacitor?: { getPlatform: () => string } };
    const platform = win.Capacitor?.getPlatform();
    if (platform === "android" || platform === "ios") return platform;
  } catch {
    // Fall through
  }
  return "web";
}

/**
 * Initialize Capacitor plugins that need setup on app start.
 * Safe to call on web - all calls are guarded by isNativePlatform().
 */
export async function initializeNativePlugins(): Promise<void> {
  if (!isNativePlatform()) return;

  try {
    const { StatusBar, Style } = await import("@capacitor/status-bar");
    await StatusBar.setBackgroundColor({ color: "#4caf50" });
    await StatusBar.setStyle({ style: Style.Light });
  } catch {
    // StatusBar plugin not available
  }

  try {
    const { Keyboard } = await import("@capacitor/keyboard");
    // Keyboard plugin auto-handles resize with config
    void Keyboard;
  } catch {
    // Keyboard plugin not available
  }
}

/**
 * Set up mobile app lifecycle handlers (back button, pause/resume).
 */
export async function setupLifecycleHandlers(onBack: () => void): Promise<void> {
  if (!isNativePlatform()) return;

  try {
    // @capacitor/app may not be installed in all environments
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const { App } = (await import("@capacitor/app" as any)) as {
      App: { addListener: (event: string, cb: () => void) => void };
    };

    // Handle Android back button
    App.addListener("backButton", () => {
      onBack();
    });
  } catch {
    // App plugin not available
  }
}
