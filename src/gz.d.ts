// Los ficheros de datos se meten en main.js como texto en base64 (ver esbuild.config.mjs).
declare module "*.json.gz" {
	const base64: string;
	export default base64;
}
