import "@testing-library/jest-dom";

if (typeof navigator.sendBeacon === "undefined") {
  Object.defineProperty(navigator, "sendBeacon", {
    value: () => true,
    writable: true,
  });
}
