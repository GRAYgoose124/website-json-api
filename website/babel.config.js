export default {
  presets: [
    ['@babel/preset-env', {
      targets: {
        node: 'current',
      },
      modules: false,
    }],
  ],
  plugins: [
    ['@babel/plugin-syntax-import-meta'],
  ],
}; 