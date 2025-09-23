const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = {
    mode: 'production',
    entry: {
        'hub/hub': './src/hub/hub.ts',
        'tab/tab': './src/tab/tab.ts',
        'widgets/throughput/throughput': './src/widgets/throughput/throughput.ts',
        'widgets/leadtime/leadtime': './src/widgets/leadtime/leadtime.ts',
        'widgets/effort/effort': './src/widgets/effort/effort.ts',
        'widgets/guardrails/guardrails': './src/widgets/guardrails/guardrails.ts',
        'services/connection': './src/services/connection.ts'
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: '[name].js',
        library: '[name]',
        libraryTarget: 'amd'
    },
    resolve: {
        extensions: ['.ts', '.tsx', '.js', '.jsx'],
        alias: {
            '@': path.resolve(__dirname, 'src'),
            'azure-devops-extension-sdk': path.resolve(__dirname, 'node_modules/azure-devops-extension-sdk'),
            'azure-devops-extension-api': path.resolve(__dirname, 'node_modules/azure-devops-extension-api')
        }
    },
    module: {
        rules: [
            {
                test: /\.tsx?$/,
                use: [
                    {
                        loader: 'ts-loader',
                        options: {
                            configFile: 'tsconfig.json'
                        }
                    }
                ],
                exclude: /node_modules/
            },
            {
                test: /\.css$/,
                use: ['style-loader', 'css-loader']
            },
            {
                test: /\.(png|jpg|jpeg|gif|svg)$/,
                type: 'asset/resource'
            },
            {
                test: /\.(woff|woff2|eot|ttf|otf)$/,
                type: 'asset/resource'
            }
        ]
    },
    plugins: [
        new CopyWebpackPlugin({
            patterns: [
                { from: 'src/hub/hub.html', to: 'hub/' },
                { from: 'src/tab/tab.html', to: 'tab/' },
                { from: 'src/widgets/*/widget.html', to: 'widgets/[1]/' },
                { from: 'src/services/connection.html', to: 'services/' },
                { from: 'vss-extension.json', to: '.' },
                { from: 'tasks/**/*', to: '.' },
                { from: 'scripts/**/*', to: '.' },
                { from: 'images/**/*', to: '.' },
                { from: 'README.md', to: '.' }
            ]
        }),
        new webpack.DefinePlugin({
            'process.env.NODE_ENV': JSON.stringify(process.env.NODE_ENV || 'production')
        })
    ],
    externals: {
        'VSS/SDK/Services/ExtensionData': 'VSS/SDK/Services/ExtensionData',
        'VSS/SDK/Services/Navigation': 'VSS/SDK/Services/Navigation',
        'VSS/Service': 'VSS/Service',
        'VSS/WebApi/RestClient': 'VSS/WebApi/RestClient',
        'TFS/Core/RestClient': 'TFS/Core/RestClient',
        'TFS/WorkItemTracking/RestClient': 'TFS/WorkItemTracking/RestClient',
        'TFS/Build/RestClient': 'TFS/Build/RestClient',
        'VSS/Common/Contracts/FormInput': 'VSS/Common/Contracts/FormInput',
        'VSS/Controls': 'VSS/Controls',
        'VSS/Controls/Grids': 'VSS/Controls/Grids',
        'VSS/Controls/Charts': 'VSS/Controls/Charts'
    },
    optimization: {
        minimize: true,
        splitChunks: {
            chunks: 'all',
            cacheGroups: {
                common: {
                    name: 'common',
                    chunks: 'all',
                    minChunks: 2,
                    enforce: true
                }
            }
        }
    },
    devtool: 'source-map'
};