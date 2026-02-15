import { Component, OnInit, OnDestroy } from '@angular/core';
import { WiregasmService } from '@app/services/wiregasm.service';
import { Subscription, interval } from 'rxjs';
import { switchMap, catchError } from 'rxjs/operators';
import { of } from 'rxjs';


@Component({
  selector: 'pcap-uploader',
  templateUrl: './pcap-uploader.component.html',
  styleUrls: ['./pcap-uploader.component.scss']
})

export class PcapUploaderComponent implements OnInit, OnDestroy {
  data: any;
  filename: string = '';
  inProgress = false;
  isDataTimeNow: any = false;
  parsingProgress = 0;
  private subscription: Subscription = new Subscription();
  private processedFiles: Set<string> = new Set();

  constructor(
    private webSharkDataService: WiregasmService
  ) { }

  private processFile(file: any) {
    // Check if we've already processed this file
    const fileId = `${file.name}-${file.size}-${file.lastModified}`;
    if (this.processedFiles.has(fileId)) {
      return;
    }

    this.processedFiles.add(fileId);
    this.filename = file.name;
    this.inProgress = true;
    this.parsingProgress = 0;
    this.webSharkDataService.postFile(file, this.isDataTimeNow).subscribe(() => {
      // File posted, now wait for processing updates
    }, (error: any) => {
      console.log(error);
      this.inProgress = false;
    });
  }

  private checkForPcapFiles() {
    // Check for auto.pcap
    return fetch('/assets/auto.pcap', { cache: 'no-cache' })
      .then(response => {
        if (response.ok) {
          return response.blob();
        }
        throw new Error('File not found');
      })
      .then(blob => {
        const file = new File([blob], 'auto.pcap', { type: 'application/octet-stream' });
        // Add lastModified to make it unique
        Object.defineProperty(file, 'lastModified', { value: Date.now() });
        this.processFile(file);
      })
      .catch(err => {
        // File not found, ignore
      });
  }

  ngOnInit() {
    // Listen to wiregasm service updates for progress
    this.subscription.add(
      this.webSharkDataService.listen().subscribe((data: any) => {
        if (data?.isParsing) {
          this.parsingProgress = Math.round(data.parsingProgress);
        }
        if (data?.type === 'processed') {
          this.inProgress = false;
          this.parsingProgress = 100;
        }
      })
    );

    // Check for PCAP files immediately
    this.checkForPcapFiles();

    // Check for new PCAP files every 5 seconds
    this.subscription.add(
      interval(5000).pipe(
        switchMap(() => {
          return this.checkForPcapFiles();
        }),
        catchError(() => of(null))
      ).subscribe()
    );
  }

  ngOnDestroy() {
    this.subscription.unsubscribe();
  }
}
