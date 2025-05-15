import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "ORSTools",
  description: "The QGIS plugin for the openrouteservice",
  themeConfig: {
    // https://vitepress.dev/reference/default-theme-config
    nav: [
      { text: 'Home', link: '/' },
      { text: 'General', link: '/general/provider_settings' },
      { text: 'Algorithms', link: '/processing_algorithms/directions_from_points_1_layer' }
    ],

    sidebar: [
      {
          text: 'General',
          items: [
            { text: 'Provider Settings', link: '/general/provider_settings'}
          ]
      },
      {
        text: 'Algorithms',
        items: [
          { text: 'Directions from Points (1)', link: '/processing_algorithms/directions_from_points_1_layer' },
          { text: 'Directions from Polylines Layer', link: '/processing_algorithms/directions_from_polylines_layer' },
          { text: 'Directions from Points (2)', link: '/processing_algorithms/directions_from_points_2_layers' },
          { text: 'Isochrones from Point', link: '/processing_algorithms/isochrones_from_point' },
          { text: 'Isochrones from Layer', link: '/processing_algorithms/isochrones_from_layer' },
          { text: 'Matrix from Layers', link: '/processing_algorithms/matrix_from_layers' }
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vuejs/vitepress' }
    ]
  }
})
