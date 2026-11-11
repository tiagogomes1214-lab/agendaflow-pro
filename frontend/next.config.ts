import type { NextConfig } from "next";

// O navegador recebe HTML/CSS/JS estáticos; FastAPI atende /api/*.
// Assim Next.js NÃO precisa rodar como um segundo servidor na Discloud.
const nextConfig: NextConfig = {
  output: "export",
  trailingSlash: true,
  images: { unoptimized: true },
};
export default nextConfig;
