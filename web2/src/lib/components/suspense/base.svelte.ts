export class SuspenseManager<T> {
  public updatePromise: Promise<T> | null;
  public lastError: unknown

  public constructor() {
    this.updatePromise = $state<Promise<T> | null>(null);
    this.lastError = $state(null);
  }

  public get running() {
    return this.updatePromise !== null;
  }

  public async waitFor<U extends T>(p: Promise<U>): Promise<U | undefined> {
    this.lastError = null;

    this.updatePromise = p;

    try {
      return await p;
    } catch (e) {
      this.lastError = e;
    } finally {
      const delay = this.lastError ? 2500 : 800
      setTimeout(() => {
        if (this.updatePromise === p) {
          this.updatePromise = null;
        }
      }, delay);
    }
  }
}