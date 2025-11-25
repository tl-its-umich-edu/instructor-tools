import * as path from 'path';
import * as webpack from 'webpack';
import BundleTrackerPlugin from 'webpack-bundle-tracker';
import MiniCssExtractPlugin from 'mini-css-extract-plugin';

const frontendPath = path.resolve(__dirname, '..');

const commonConfig: webpack.Configuration = {
  context: frontendPath,
  entry: path.resolve('app', 'index'),
  output: {
    path: path.resolve('./bundles/'),
    filename: '[name]-[fullhash].js',
    chunkFilename: '[name]-[chunkhash].js',
    clean: true,
  },

  plugins: [
    new BundleTrackerPlugin({ path: frontendPath, filename: 'webpack-stats.json' }),
    new MiniCssExtractPlugin({
      filename: '[name]-[fullhash].css',
      chunkFilename: '[name]-[chunkhash].css',
    }),
  ],

  module: {
    rules: [
      {
        test: /\.(tsx|ts)?$/,
        exclude: /node_modules/,
        use: {
          loader: 'ts-loader',
          options: {
            configFile: path.resolve(frontendPath, 'tsconfig.json')
          }
        }
      },
      {
        test: /\.css$/,
        use: [MiniCssExtractPlugin.loader, 'css-loader'],
      }
    ],
  },

  resolve: {
    modules: ['node_modules'],
    extensions: ['.ts', '.tsx', '.js', '.jsx']
  },

  optimization: {
    runtimeChunk: 'single',
    splitChunks: {
      chunks: 'all',
      maxSize: 244000,
      cacheGroups: {
        vendor: {
          test: /[\\/]node_modules[\\/]/,
          name: 'vendors',
          chunks: 'all',
        },
      },
    },
  },
};

export default commonConfig;
