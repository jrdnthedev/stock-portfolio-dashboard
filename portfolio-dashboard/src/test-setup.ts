import { getTestBed } from '@angular/core/testing';
import {
  BrowserDynamicTestingModule,
  platformBrowserDynamicTesting,
} from '@angular/platform-browser-dynamic/testing';
import { expect } from 'vitest';
import * as axeCore from 'axe-core';

// Initialize Angular testing environment
getTestBed().initTestEnvironment(BrowserDynamicTestingModule, platformBrowserDynamicTesting());

// Custom axe accessibility matcher
expect.extend({
  async toBeAccessible(received: HTMLElement) {
    const results = await axeCore.run(received);
    const violations = results.violations;

    if (violations.length === 0) {
      return {
        message: () => 'Expected element to have accessibility violations, but found none',
        pass: true,
      };
    }

    const violationMessages = violations.map((violation) => {
      const nodes = violation.nodes.map((node) => node.html).join('\n');
      return `${violation.id}: ${violation.description}\n${violation.help}\n${nodes}`;
    });

    return {
      message: () =>
        `Expected element to be accessible, but found ${violations.length} violation(s):\n\n${violationMessages.join('\n\n')}`,
      pass: false,
    };
  },
});

// Extend Vitest's expect type
declare module 'vitest' {
  interface Assertion {
    toBeAccessible(): Promise<void>;
  }
  interface AsymmetricMatchersContaining {
    toBeAccessible(): Promise<void>;
  }
}
