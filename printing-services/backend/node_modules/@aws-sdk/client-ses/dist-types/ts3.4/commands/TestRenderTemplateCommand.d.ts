import { Command as $Command } from "@smithy/smithy-client";
import { MetadataBearer as __MetadataBearer } from "@smithy/types";
import {
  TestRenderTemplateRequest,
  TestRenderTemplateResponse,
} from "../models/models_0";
import {
  ServiceInputTypes,
  ServiceOutputTypes,
  SESClientResolvedConfig,
} from "../SESClient";
export { __MetadataBearer };
export { $Command };
export interface TestRenderTemplateCommandInput
  extends TestRenderTemplateRequest {}
export interface TestRenderTemplateCommandOutput
  extends TestRenderTemplateResponse,
    __MetadataBearer {}
declare const TestRenderTemplateCommand_base: {
  new (
    input: TestRenderTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    TestRenderTemplateCommandInput,
    TestRenderTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  new (
    input: TestRenderTemplateCommandInput
  ): import("@smithy/smithy-client").CommandImpl<
    TestRenderTemplateCommandInput,
    TestRenderTemplateCommandOutput,
    SESClientResolvedConfig,
    ServiceInputTypes,
    ServiceOutputTypes
  >;
  getEndpointParameterInstructions(): import("@smithy/middleware-endpoint").EndpointParameterInstructions;
};
export declare class TestRenderTemplateCommand extends TestRenderTemplateCommand_base {
  protected static __types: {
    api: {
      input: TestRenderTemplateRequest;
      output: TestRenderTemplateResponse;
    };
    sdk: {
      input: TestRenderTemplateCommandInput;
      output: TestRenderTemplateCommandOutput;
    };
  };
}
