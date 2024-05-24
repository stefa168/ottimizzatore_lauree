import {browser} from "$app/environment";

export class Poller<T> {
    readonly interval: number;
    private endpoint: string;
    private callback: (data: T) => void;
    readonly errorHandler: (error: Error) => void;
    private intervalId: number | null;

    constructor(endpoint: string, interval: number, callback: (data: T) => void, errorHandler: (error: Error) => void) {
        this.interval = interval;
        this.endpoint = endpoint;
        this.callback = callback;
        this.errorHandler = errorHandler;
        this.intervalId = null;
    }

    start() {
        if (!browser) return;
        this.intervalId = window.setInterval(() => {
            fetch(this.endpoint)
                .then(response => {
                    if (!response.ok) {
                        throw new Error(`Failed to fetch data: ${response.statusText}`);
                    }
                    return response.json();
                })
                .then(data => {
                    this.callback(data);
                })
                .catch(error => {
                    this.errorHandler(error);
                });
        }, this.interval);
    }

    stop() {
        if (!browser) return;
        if (this.intervalId !== null) {
            window.clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
}