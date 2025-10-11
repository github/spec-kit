import {
  AwsSdkSigV4AuthInputConfig,
  AwsSdkSigV4AuthResolvedConfig,
  AwsSdkSigV4PreviouslyResolved,
} from "@aws-sdk/core";
import {
  HandlerExecutionContext,
  HttpAuthScheme,
  HttpAuthSchemeParameters,
  HttpAuthSchemeParametersProvider,
  HttpAuthSchemeProvider,
  Provider,
} from "@smithy/types";
import { SESClientResolvedConfig } from "../SESClient";
export interface SESHttpAuthSchemeParameters extends HttpAuthSchemeParameters {
  region?: string;
}
export interface SESHttpAuthSchemeParametersProvider
  extends HttpAuthSchemeParametersProvider<
    SESClientResolvedConfig,
    HandlerExecutionContext,
    SESHttpAuthSchemeParameters,
    object
  > {}
export declare const defaultSESHttpAuthSchemeParametersProvider: (
  config: SESClientResolvedConfig,
  context: HandlerExecutionContext,
  input: object
) => Promise<SESHttpAuthSchemeParameters>;
export interface SESHttpAuthSchemeProvider
  extends HttpAuthSchemeProvider<SESHttpAuthSchemeParameters> {}
export declare const defaultSESHttpAuthSchemeProvider: SESHttpAuthSchemeProvider;
export interface HttpAuthSchemeInputConfig extends AwsSdkSigV4AuthInputConfig {
  authSchemePreference?: string[] | Provider<string[]>;
  httpAuthSchemes?: HttpAuthScheme[];
  httpAuthSchemeProvider?: SESHttpAuthSchemeProvider;
}
export interface HttpAuthSchemeResolvedConfig
  extends AwsSdkSigV4AuthResolvedConfig {
  readonly authSchemePreference: Provider<string[]>;
  readonly httpAuthSchemes: HttpAuthScheme[];
  readonly httpAuthSchemeProvider: SESHttpAuthSchemeProvider;
}
export declare const resolveHttpAuthSchemeConfig: <T>(
  config: T & HttpAuthSchemeInputConfig & AwsSdkSigV4PreviouslyResolved
) => T & HttpAuthSchemeResolvedConfig;
