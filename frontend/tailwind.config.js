/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./components/**/*.{js,vue,ts}",
    "./layouts/**/*.vue",
    "./pages/**/*.vue",
    "./plugins/**/*.{js,ts}",
    "./nuxt.config.{js,ts}",
    "./app.vue",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Montserrat', 'sans-serif'], // Add Montserrat here
      },
      colors: {
        'primary': 'orange', 
        'secondary': '#A9A9A9', 
        'accent': '#808080',    
        'base': '#000000',
        'neon-pink': '#FF00FF',
        'neon-blue': '#00FFFF',
      },
      boxShadow: { // Add neon shadow effects
        'neon-pink': '0 0 5px #FF00FF, 0 0 10px #FF00FF, 0 0 20px #FF00FF, 0 0 40px #FF00FF',
        'neon-blue': '0 0 5px #00FFFF, 0 0 10px #00FFFF, 0 0 20px #00FFFF, 0 0 40px #00FFFF',
      }
    },
  },
  plugins: [],
}