export default function AboutPage() {
  return (
    <div className="max-w-2xl prose">
      <h1 className="text-2xl font-bold text-leaf-800">About Smart Plant Doctor</h1>
      <p>
        AI + IoT plant health platform combining realtime ESP32 sensor monitoring with
        deep-learning disease detection and personalized care recommendations.
      </p>
      <h2 className="text-lg font-semibold mt-4">Stack</h2>
      <ul className="list-disc ml-5 text-sm">
        <li>React PWA frontend (Vercel)</li>
        <li>FastAPI backend + PostgreSQL (Railway/Render)</li>
        <li>MobileNetV2 / EfficientNet disease classifier</li>
        <li>ESP32 sensors with device onboarding</li>
      </ul>
    </div>
  );
}
