package com.wfsample.notification;

import com.wfsample.service.NotificationApi;

import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.atomic.AtomicInteger;

import javax.ws.rs.core.Response;

import io.opentracing.Scope;
import io.opentracing.Span;
import io.opentracing.SpanContext;
import io.opentracing.Tracer;
import io.opentracing.contrib.concurrent.TracedExecutorService;
import io.opentracing.propagation.Format;
import io.opentracing.propagation.TextMap;
import io.opentracing.propagation.TextMapExtractAdapter;
import io.opentracing.propagation.TextMapInjectAdapter;
import io.opentracing.tag.Tags;
import io.opentracing.util.GlobalTracer;

/**
 * Implementation of Notification Service.
 *
 * @author Hao Song (songhao@vmware.com).
 */
@Service
public class NotificationService implements NotificationApi {
  private AtomicInteger notify = new AtomicInteger(0);

  private final Tracer tracer;

  @Autowired
  public NotificationService() {
    this.tracer = GlobalTracer.get();
  }

  public Response notify(String trackNum) {
    Span currentSpan = tracer.scopeManager().active().span();
    TextMap carrier = new TextMapInjectAdapter(new HashMap<>());
    tracer.inject(currentSpan.context(), Format.Builtin.HTTP_HEADERS, carrier);
    ExecutorService executorService = new TracedExecutorService(
        Executors.newFixedThreadPool(1), tracer);
    executorService.submit(new InternalNotifyService());
    return Response.accepted().build();
  }

  class InternalNotifyService implements Runnable {

    @Override
    public void run() {
      TextMap carrier = new TextMapExtractAdapter(new HashMap<>());
      SpanContext ctx = tracer.extract(Format.Builtin.HTTP_HEADERS, carrier);
      try (Scope asyncSpan = tracer.buildSpan("asyncNotify").asChildOf(ctx).
          startActive(true)) {
        try {
          Thread.sleep(200);
          if (notify.incrementAndGet() % 10 == 0) {
            Tags.ERROR.set(asyncSpan.span(), true);
          }
        } catch (InterruptedException e) {
          e.printStackTrace();
        }
      }
    }
  }

}