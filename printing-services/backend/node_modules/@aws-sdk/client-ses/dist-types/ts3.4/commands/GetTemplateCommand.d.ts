import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import { GetTemplateRequest, GetTemplateResponse } from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface GetTemplateCommandInput extends GetTemplateRequest {}
export interface GetTemplateCommandOutput
  extends GetTemplateResponse,
    __MetadataBearer {}
declare const GetTemplateCommand_base: {
  new (
    input: GetTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetTemplateCommandInput,
    GetTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: GetTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    GetTemplateCommandInput,
    GetTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class GetTemplateCommand extends GetTemplateCommand_base {
  protected static __types: {
    api: {
      input: GetTemplateRequest;
      output: GetTemplateResponse;
    };
    sdk: {
      input: GetTemplateCommandInput;
      output: GetTemplateCommandOutput;
    };
  };
}
