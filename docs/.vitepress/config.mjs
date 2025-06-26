import { defineConfig } from 'vitepress'

// https://vitepress.dev/reference/site-config
export default defineConfig({
  title: "ORSTools",
  description: "The QGIS plugin for the openrouteservice",
  base: "/orstools-qgis-plugin/",
  head: [
    ['link', { rel: 'icon', type: 'image/png', href: '/icon_orstools.png' }]
  ],
  themeConfig: {
    logo: '/img/icon_orstools.png',
    sidebar: [
      {
        text: 'General',
        items: [
          { text: 'Installation and Setup', link: '/installation_and_setup' },
          { text: 'General Usage', link: '/usage' },
          { text: 'Developer Information', link: '/developer_information' }
        ]
      },
      {
        text: 'Processing Tools',
        items: [
          { text: 'Overview', link: '/processing_algorithms/processing_overview' },
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
