/** @type {import('tailwindcss').Config} */
module.exports = {
  content: ["./templates/**/*.html", "./static/**/*.js"],
  theme: {
    extend: {
      fontFamily: {
        custom: ['gaming'], 
      },
    },
  },
  plugins: [require("daisyui")],
  daisyui: {
    themes: [ 
       {
      "custom-theme": {
        primary: "#2eade3",
        secondary: "#fcfcfc",
        accent: "#303030",
        neutral: "#2eade3",
        "base-100": "#000000",
        },
      },
    ],
  },
};
